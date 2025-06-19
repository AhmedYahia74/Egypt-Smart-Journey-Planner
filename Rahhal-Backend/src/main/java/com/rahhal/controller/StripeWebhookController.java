package com.rahhal.controller;

import com.rahhal.entity.Payment;
import com.rahhal.entity.Tourist;
import com.rahhal.entity.Trip;
import com.rahhal.repository.PaymentRepository;
import com.rahhal.repository.TouristRepository;
import com.rahhal.repository.TripRepository;
import com.rahhal.service.EmailService;
import com.stripe.exception.SignatureVerificationException;
import com.stripe.model.Event;
import com.stripe.model.PaymentIntent;
import com.stripe.model.StripeObject;
import com.stripe.model.checkout.Session;
import com.stripe.net.Webhook;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/webhooks/stripe")
@Slf4j
public class StripeWebhookController {

    @Value("${stripe.webhook.secret}")
    private String endpointSecret;
    private final TripRepository tripRepository;
    private final TouristRepository touristRepository;
    private final PaymentRepository paymentRepository;
    private final EmailService emailService;

    public StripeWebhookController(TripRepository tripRepository, TouristRepository touristRepository, PaymentRepository paymentRepository, EmailService emailService) {
        this.tripRepository = tripRepository;
        this.touristRepository = touristRepository;
        this.paymentRepository = paymentRepository;
        this.emailService = emailService;
    }

    @PostMapping
    public ResponseEntity<String> handleStripeEvent(@RequestBody String payload,
                                                    @RequestHeader("Stripe-Signature") String sigHeader) {
        try {
            Event event = Webhook.constructEvent(
                    payload, sigHeader, endpointSecret
            );

            switch (event.getType()) {
                case "checkout.session.completed":
                    handleCheckoutCompleted(event);
                    break;
                case "payment_intent.payment_failed":
                    handlePaymentFailure(event);
                    break;
                default:
                    log.warn("Unhandled event type: {}", event.getType());
            }

            return ResponseEntity.ok("");

        } catch (SignatureVerificationException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Invalid signature");
        }
    }

    @GetMapping("/success")
    public ResponseEntity<String> handleSuccess(@RequestParam("session_id") String sessionId) {
        try {
            log.info("Processing success for session: {}", sessionId);
            
            // First check if payment was already processed
            if (paymentRepository.existsBySessionId(sessionId)) {
                log.info("Payment already processed for session: {}", sessionId);
                return ResponseEntity.ok("Payment already processed successfully!");
            }
            
            // Try to retrieve the session from Stripe
            Session session;
            try {
                session = Session.retrieve(sessionId);
            } catch (Exception e) {
                log.error("Could not retrieve session {} from Stripe: {}", sessionId, e.getMessage());
                
                // If we can't retrieve the session, we can't process the payment
                // This could happen if the session expired or was created with different keys
                return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body("Could not verify payment. Please contact support if you believe this is an error.");
            }
            
            if ("complete".equals(session.getStatus())) {
                // Process the payment
                processPaymentFromSession(session);
                return ResponseEntity.ok("Payment processed successfully!");
            } else {
                log.warn("Session {} is not complete. Status: {}", sessionId, session.getStatus());
                return ResponseEntity.badRequest().body("Payment not completed. Status: " + session.getStatus());
            }
            
        } catch (Exception e) {
            log.error("Error processing success for session: {}", sessionId, e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("Error processing payment. Please contact support.");
        }
    }

    @GetMapping("/success-alt")
    public ResponseEntity<String> handleSuccessAlternative(
            @RequestParam("session_id") String sessionId,
            @RequestParam("trip_id") String tripId,
            @RequestParam("tourist_id") String touristId,
            @RequestParam("tickets") String numberOfTickets) {
        try {
            log.info("Processing success (alternative) for session: {} with params: tripId={}, touristId={}, tickets={}", 
                    sessionId, tripId, touristId, numberOfTickets);
            
            // First check if payment was already processed
            if (paymentRepository.existsBySessionId(sessionId)) {
                log.info("Payment already processed for session: {}", sessionId);
                return ResponseEntity.ok("Payment already processed successfully!");
            }
            
            // Process the payment using URL parameters
            processPaymentFromParams(sessionId, tripId, touristId, numberOfTickets);
            return ResponseEntity.ok("Payment processed successfully!");
            
        } catch (Exception e) {
            log.error("Error processing success (alternative) for session: {}", sessionId, e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("Error processing payment. Please contact support.");
        }
    }

    @GetMapping("/cancel")
    public ResponseEntity<String> handleCancel(@RequestParam(value = "session_id", required = false) String sessionId) {
        try {
            log.info("Payment cancelled for session: {}", sessionId);
            
            if (sessionId != null) {
                // Try to retrieve session and restore seats if possible
                try {
                    Session session = Session.retrieve(sessionId);
                    Map<String, String> metadata = session.getMetadata();
                    
                    if (metadata != null && metadata.containsKey("tripId") && metadata.containsKey("numberOfTickets")) {
                        int tripId = Integer.parseInt(metadata.get("tripId"));
                        int ticketCount = Integer.parseInt(metadata.get("numberOfTickets"));
                        
                        Trip trip = tripRepository.findById(tripId)
                                .orElseThrow(() -> new RuntimeException("Trip not found"));
                        
                        // Restore available seats
                        trip.setAvailableSeats(trip.getAvailableSeats() + ticketCount);
                        tripRepository.save(trip);
                        
                        log.info("Restored {} seats for trip {}", ticketCount, tripId);
                    }
                } catch (Exception e) {
                    log.warn("Could not restore seats for cancelled session: {}", sessionId, e);
                }
            }
            
            return ResponseEntity.ok("Payment cancelled successfully");
            
        } catch (Exception e) {
            log.error("Error handling cancel for session: {}", sessionId, e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error handling cancellation");
        }
    }

    private void handleCheckoutCompleted(Event event) {
        Optional<StripeObject> obj = event.getDataObjectDeserializer().getObject();
        if (obj.isEmpty() || !(obj.get() instanceof Session session)) {
            log.error("Invalid object for checkout.session.completed");
            return;
        }

        processPaymentFromSession(session);
    }

    private void processPaymentFromSession(Session session) {
        Map<String, String> metadata = session.getMetadata();
        String sessionId = session.getId();
    
        // Avoid processing duplicate payments
        if (paymentRepository.existsBySessionId(sessionId)) {
            log.info("Payment already processed for session: {}", sessionId);
            return;
        }
    
        int tripId = Integer.parseInt(metadata.get("tripId"));
        int ticketCount = Integer.parseInt(metadata.get("numberOfTickets"));
        int touristId = Integer.parseInt(metadata.get("touristId"));
    
        Trip trip = tripRepository.findById(tripId)
                .orElseThrow(() -> new RuntimeException("Trip not found"));
        Tourist tourist = touristRepository.findById(touristId)
                .orElseThrow(() -> new RuntimeException("Tourist not found"));
    
        // Save payment record
        Payment payment = Payment.builder()
                .tourist(tourist)
                .trip(trip)
                .amount(ticketCount)
                .sessionId(sessionId)
                .build();
        paymentRepository.save(payment);
    
        // Update trip seats
        trip.setAvailableSeats(trip.getAvailableSeats() - ticketCount);
        tripRepository.save(trip);
    
        // Send confirmation email to tourist
        String subject = "Your Ticket Confirmation for " + trip.getTitle();
        String body = String.format("""
                Dear %s,
    
                Thank you for booking %d ticket(s) for the trip: %s.
    
                Trip Details:
                - Date: %s
                - Company: %s
    
                We hope you enjoy your trip!
    
                Best regards,
                The Rahhal Team
                """,
                tourist.getName(),
                ticketCount,
                trip.getTitle(),
                trip.getDate(),
                trip.getCompany().getName()
        );
        emailService.sendEmail(tourist.getEmail(), subject, body);
    
        // Send booking notification to the trip's company
        String companySubject = "New Booking Received: " + trip.getTitle();
        String companyBody = String.format("""
                Hello,
    
                A new booking has been made for your trip: %s.
    
                Booking Details:
                - Tourist Name: %s
                - Tourist Email: %s
                - Tickets Booked: %d
                - Trip Date: %s
    
                Please prepare accordingly.
    
                Regards,
                Rahhal System
                """,
                trip.getTitle(),
                tourist.getName(),
                tourist.getEmail(),
                ticketCount,
                trip.getDate()
        );
        emailService.sendEmail(trip.getCompany().getEmail(), companySubject, companyBody);
    
        log.info("Payment processed successfully for session: {}, trip: {}, tourist: {}", 
                sessionId, tripId, touristId);
    }
    

    private void handlePaymentFailure(Event event) {
        Optional<StripeObject> obj = event.getDataObjectDeserializer().getObject();
        if (obj.isEmpty() || !(obj.get() instanceof PaymentIntent paymentIntent)) {
            log.error("Invalid object for payment failure");
            return;
        }

        Map<String, String> metadata = paymentIntent.getMetadata();

        String tripId = metadata.get("tripId");
        String tickets = metadata.get("numberOfTickets");

        log.error("Payment failed for tripId={}, numberOfTickets={}", tripId, tickets);

        Trip trip = tripRepository.findById(Integer.parseInt(tripId))
                .orElseThrow(() -> new RuntimeException("Trip not found"));

        trip.setAvailableSeats(trip.getAvailableSeats() + Integer.parseInt(tickets));
        tripRepository.save(trip);
    }

    private void processPaymentFromParams(String sessionId, String tripId, String touristId, String numberOfTickets) {
        // Check if payment was already processed
        if (paymentRepository.existsBySessionId(sessionId)) {
            log.info("Payment already processed for session: {}", sessionId);
            return;
        }

        int tripIdInt = Integer.parseInt(tripId);
        int ticketCount = Integer.parseInt(numberOfTickets);
        int touristIdInt = Integer.parseInt(touristId);

        Trip trip = tripRepository.findById(tripIdInt)
                .orElseThrow(() -> new RuntimeException("Trip not found"));

        Tourist tourist = touristRepository.findById(touristIdInt)
                .orElseThrow(() -> new RuntimeException("Tourist not found"));

        Payment payment = Payment.builder()
                .tourist(tourist)
                .trip(trip)
                .amount(ticketCount)
                .sessionId(sessionId)
                .build();

        paymentRepository.save(payment);

        // Update available seats
        trip.setAvailableSeats(trip.getAvailableSeats() - ticketCount);
        tripRepository.save(trip);

        // Send ticket email to tourist
        String subject = "Your Ticket for " + trip.getTitle();
        String body = "Dear " + tourist.getName() + ",\n\n"
            + "Thank you for booking " + ticketCount + " ticket(s) for the trip: " + trip.getTitle() + ".\n"
            + "Trip Date: " + trip.getDate() + "\n"
            + "Company: " + trip.getCompany().getName() + "\n\n"
            + "Enjoy your trip!\n\nRahhal Team";
        emailService.sendEmail(tourist.getEmail(), subject, body);

        // Send booking notification to company
        String companyBody = "A new booking has been made for your trip: " + trip.getTitle() + ".\n"
            + "Tourist: " + tourist.getName() + " (" + tourist.getEmail() + ")\n"
            + "Tickets: " + ticketCount + "\n"
            + "Trip Date: " + trip.getDate() + "\n";
        emailService.sendEmail(trip.getCompany().getEmail(), "New Booking: " + trip.getTitle(), companyBody);

        log.info("Payment processed successfully (alternative) for session: {}, trip: {}, tourist: {}", 
                sessionId, tripIdInt, touristIdInt);

        // TODO: Notify tourist and company
    }
}

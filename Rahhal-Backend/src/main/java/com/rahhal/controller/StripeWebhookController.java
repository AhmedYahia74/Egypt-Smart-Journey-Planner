package com.rahhal.controller;

import com.rahhal.entity.Payment;
import com.rahhal.entity.Tourist;
import com.rahhal.entity.Trip;
import com.rahhal.repository.PaymentRepository;
import com.rahhal.repository.TouristRepository;
import com.rahhal.repository.TripRepository;
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

    public StripeWebhookController(TripRepository tripRepository, TouristRepository touristRepository, PaymentRepository paymentRepository) {
        this.tripRepository = tripRepository;
        this.touristRepository = touristRepository;
        this.paymentRepository = paymentRepository;
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

    private void handleCheckoutCompleted(Event event) {
        Optional<StripeObject> obj = event.getDataObjectDeserializer().getObject();
        if (obj.isEmpty() || !(obj.get() instanceof Session session)) {
            log.error("Invalid object for checkout.session.completed");
            return;
        }

        Map<String, String> metadata = session.getMetadata();

        int tripId = Integer.parseInt(metadata.get("tripId"));
        int ticketCount = Integer.parseInt(metadata.get("numberOfTickets"));
        int touristId = Integer.parseInt(metadata.get("touristId"));

        Trip trip = tripRepository.findById(tripId)
                .orElseThrow(() -> new RuntimeException("Trip not found"));

        Tourist tourist = touristRepository.findById(touristId)
                .orElseThrow(() -> new RuntimeException("Tourist not found"));

        Payment payment = Payment.builder()
                .tourist(tourist)
                .trip(trip)
                .amount(ticketCount)
                .build();

        paymentRepository.save(payment);

        // TODO: Notify tourist and company
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

}

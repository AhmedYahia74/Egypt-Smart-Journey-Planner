package com.rahhal.controller;

import com.rahhal.entity.Trip;
import com.rahhal.repository.TripRepository;
import com.stripe.exception.SignatureVerificationException;
import com.stripe.model.Event;
import com.stripe.model.checkout.Session;
import com.stripe.net.Webhook;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/webhooks/stripe")
@Slf4j
public class StripeWebhookController {

    @Value("${stripe.webhook.secret}")
    private String endpointSecret;
    private final TripRepository tripRepository;

    public StripeWebhookController(TripRepository tripRepository) {
        this.tripRepository = tripRepository;
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
                case "payment_intent.payment_failed", "checkout.session.expired":
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
        Session session = (Session) event.getDataObjectDeserializer().getObject().get();
        Map<String, String> metaData = session.getMetadata();
        log.info("Checkout session completed for session: {}");

        // TODO: notify Tourist and company

    }

    private void handlePaymentFailure(Event event) {
        Session session = (Session) event.getDataObjectDeserializer().getObject().get();
        Map<String, String> metaData = session.getMetadata();
        log.error("Payment failed for session: {}", session.getId());

        Trip trip = tripRepository.findById(Integer.parseInt(metaData.get("tripId")))
                .orElseThrow(() -> new RuntimeException("Trip not found"));

        trip.setAvailableSeats(trip.getAvailableSeats() + Integer.parseInt(metaData.get("numberOfTickets")));
        tripRepository.save(trip);

        //TODO: handle isBooked Column as in case of this payment is the first payment to this trip column should return to be false
    }

}

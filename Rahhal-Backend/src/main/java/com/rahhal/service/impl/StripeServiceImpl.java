package com.rahhal.service.impl;

import com.rahhal.dto.BookingRequestDTO;
import com.rahhal.repository.CompanyProfileRepository;
import com.rahhal.service.StripeService;
import com.stripe.Stripe;
import com.stripe.exception.StripeException;
import com.stripe.model.Account;
import com.stripe.model.checkout.Session;
import com.stripe.net.RequestOptions;
import com.stripe.param.AccountCreateParams;
import com.stripe.param.AccountLinkCreateParams;
import com.stripe.param.checkout.SessionCreateParams;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class StripeServiceImpl implements StripeService {
    private final CompanyProfileRepository companyProfileRepository;
    @Value("${stripe.secret-key}")
    private String stripeKey;

    public StripeServiceImpl(CompanyProfileRepository companyProfileRepository) {
        this.companyProfileRepository = companyProfileRepository;
    }

    @PostConstruct
    public void init() {
        Stripe.apiKey = stripeKey;
    }

    @Override
    public AccountLinkCreateParams createCompanyAccount(String email) throws StripeException {
        AccountCreateParams accountParams = AccountCreateParams.builder()
                .setType(AccountCreateParams.Type.EXPRESS)
                .setCountry("US")
                .setEmail(email)
                .setBusinessType(AccountCreateParams.BusinessType.COMPANY)
                .setBusinessProfile(AccountCreateParams.BusinessProfile.builder()
                        .setName("Your Company Name")
                        .setProductDescription("Tours and travel packages")
                        .build())
                .setCapabilities(AccountCreateParams.Capabilities.builder()
                        .setTransfers(AccountCreateParams.Capabilities.Transfers.builder().setRequested(true).build())
                        .setCardPayments(AccountCreateParams.Capabilities.CardPayments.builder()
                                .setRequested(true)
                                .build())
                        .build())
                .build();

        Account account = Account.create(accountParams);

        return AccountLinkCreateParams.builder()
                .setAccount(account.getId())
                .setRefreshUrl("https://Rahhal/refresh")  // TODO: Replace with actual URL
                .setReturnUrl("https://Rahhal/onboarding/complete")
                .setType(AccountLinkCreateParams.Type.ACCOUNT_ONBOARDING)
                .build();
    }


    @Override
    public void deleteAccount(String accountId) throws StripeException {
        Account account = Account.retrieve(accountId);
        account.setDeleted(true);
    }

    @Override
    public String createSession(BookingRequestDTO bookingRequest) throws StripeException {
        long unitAmount = (long) (bookingRequest.getTrip().getPrice() * 100); // in cents
        int quantity = bookingRequest.getNumberOfTickets();

        SessionCreateParams params = SessionCreateParams.builder()
                .setMode(SessionCreateParams.Mode.PAYMENT)
                .setSuccessUrl("http://localhost:8088/api/webhooks/stripe/success-alt?session_id={CHECKOUT_SESSION_ID}&trip_id=" + bookingRequest.getTrip().getTripId() + "&tourist_id=" + bookingRequest.getTourist().getUserId() + "&tickets=" + quantity)
                .setCancelUrl("http://localhost:8088/api/webhooks/stripe/cancel")
                .setCustomerEmail(bookingRequest.getTourist().getEmail())
                .addLineItem(
                        SessionCreateParams.LineItem.builder()
                                .setQuantity((long) quantity)
                                .setPriceData(
                                        SessionCreateParams.LineItem.PriceData.builder()
                                                .setCurrency("usd")
                                                .setUnitAmount(unitAmount)
                                                .setProductData(
                                                        SessionCreateParams.LineItem.PriceData.ProductData.builder()
                                                                .setName(bookingRequest.getTrip().getTitle())
                                                                //.addImage() // TODO
                                                                .build()
                                                )
                                                .build()
                                )
                                .build()
                )
                .putMetadata("tripId", String.valueOf(bookingRequest.getTrip().getTripId()))
                .putMetadata("touristId", String.valueOf(bookingRequest.getTourist().getUserId()))
                .putMetadata("numberOfTickets", String.valueOf(quantity))
                .putMetadata("tripDate", bookingRequest.getTrip().getDate().toString())
                .build();

        log.info("Creating Stripe session for booking request: {}", bookingRequest);

        RequestOptions requestOptions = RequestOptions.builder()
                .setStripeAccount(companyProfileRepository.findStripeAccountIdByCompany(bookingRequest.getTrip().getCompany())) // The connected (company) account ID
                .build();

        log.info("Using Stripe account ID: {}", requestOptions.getStripeAccount());

        Session session = Session.create(params, requestOptions);
        return session.getUrl();
    }

}

package com.rahhal.service.Impl;

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
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
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
                .build();

        Account account = Account.create(accountParams);

        return AccountLinkCreateParams.builder()
                .setAccount(account.getId())
                .setRefreshUrl("https://Rahhal/refresh")  // TODO: Replace with actual refresh URL
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
                .setSuccessUrl("https://Rahhal/success?session_id={CHECKOUT_SESSION_ID}")
                .setCancelUrl("https://Rahhal/cancel")
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
                                                                .setDescription(bookingRequest.getTrip().getDescription())
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

        RequestOptions requestOptions = RequestOptions.builder()
                .setStripeAccount(companyProfileRepository.findStripeAccountIdByCompany(bookingRequest.getTrip().getCompany())) // The connected (company) account ID
                .build();

        Session session = Session.create(params, requestOptions);
        return session.getUrl();
    }

}

package com.rahhal.service;

import com.rahhal.dto.BookingRequestDTO;
import com.stripe.exception.StripeException;
import com.stripe.param.AccountLinkCreateParams;

public interface StripeService {
    AccountLinkCreateParams createCompanyAccount(String email) throws StripeException;
    void deleteAccount(String accountId) throws StripeException;

    String createSession(BookingRequestDTO bookingRequestDTO) throws StripeException;
}

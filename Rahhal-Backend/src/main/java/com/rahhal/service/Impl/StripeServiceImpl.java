package com.rahhal.service.Impl;

import com.rahhal.service.StripeService;
import com.stripe.Stripe;
import com.stripe.exception.StripeException;
import com.stripe.model.Account;
import com.stripe.param.AccountCreateParams;
import com.stripe.param.AccountLinkCreateParams;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class StripeServiceImpl implements StripeService {

    @Value("${stripe.secret-key}")
    private String stripeKey;
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
}

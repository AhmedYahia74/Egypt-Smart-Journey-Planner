package com.rahhal.service;

import com.rahhal.dto.CompanyDto;
import com.rahhal.dto.UserDto;
import com.stripe.exception.StripeException;
import com.stripe.model.AccountLink;

import java.util.List;

public interface AdminService {
    AccountLink addNewCompany(CompanyDto companyDto) throws com.stripe.exception.StripeException;
    void deleteAccount(int id) throws StripeException;
    List<UserDto> viewAllAccounts();
    void reactivateCompanyAccount(int companyId);
    void changeAccountStatus(int userId,boolean status);

}

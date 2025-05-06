package com.rahhal.service;

import com.rahhal.dto.CompanyDto;
import com.rahhal.dto.UserDto;

import java.util.List;

public interface AdminService {
    void addNewCompany(CompanyDto companyDto);
    void deleteAccount(int id);
    List<UserDto> viewAllAccounts();
    void reactivateCompanyAccount(int companyId);
    void changeAccountStatus(int userId,boolean status);

}

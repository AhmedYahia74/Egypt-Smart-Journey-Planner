package com.rahhal.service;

import com.rahhal.dto.CompanyDto;

public interface AdminService {
    void addNewCompany(CompanyDto companyDto);
    void deleteAccount(int id);
}

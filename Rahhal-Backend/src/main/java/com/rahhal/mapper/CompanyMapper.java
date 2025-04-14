package com.rahhal.mapper;

import com.rahhal.dto.CompanyDto;
import com.rahhal.entity.Company;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
public class CompanyMapper {
    private final PasswordEncoder passwordEncoder;

    public CompanyMapper(PasswordEncoder passwordEncoder) {this.passwordEncoder = passwordEncoder;}

    public Company mapToEntity(CompanyDto companyDto)
    {
        Company company=new Company();
        company.setEmail(companyDto.getEmail());
        company.setPassword(passwordEncoder.encode(companyDto.getPassword()));
        company.setName(companyDto.getName());
        return company;
    }

}

package com.rahhal.mapper;

import com.rahhal.dto.CompanyDto;
import com.rahhal.entity.Company;
import com.rahhal.entity.CompanyProfile;
import org.springframework.stereotype.Component;

@Component
public class CompanyProfileMapper {

    public CompanyProfile mapToEntity(CompanyDto companyDto,Company company) {
        return CompanyProfile.builder()
                .name(companyDto.getName())
                .userId(company.getUserId())
                .description(companyDto.getDescription())
                .stripeAccountId(companyDto.getStripeAccountId())
                .build();
    }

}

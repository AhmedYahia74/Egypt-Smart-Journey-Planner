package com.rahhal.service.impl;

import com.rahhal.dto.CompanyProfileDTO;
import com.rahhal.entity.CompanyProfile;
import com.rahhal.mapper.CompanyProfileMapper;
import com.rahhal.repository.CompanyProfileRepository;
import com.rahhal.service.CompanyProfileService;
import org.springframework.stereotype.Service;

@Service
public class CompanyProfileServiceImpl implements CompanyProfileService {

    private final CompanyProfileRepository companyProfileRepository;
    private final CompanyProfileMapper companyProfileMapper;

    public CompanyProfileServiceImpl(CompanyProfileRepository companyProfileRepository,
                                     CompanyProfileMapper companyProfileMapper) {
        this.companyProfileRepository = companyProfileRepository;
        this.companyProfileMapper = companyProfileMapper;
    }

    @Override
    public CompanyProfileDTO getCompanyProfile(String companyName) {
        CompanyProfile profile = companyProfileRepository.findByName(companyName)
                .orElseThrow(() -> new RuntimeException("Company with name " + companyName + " not found."));

        return companyProfileMapper.mapToDto(profile);
    }
}

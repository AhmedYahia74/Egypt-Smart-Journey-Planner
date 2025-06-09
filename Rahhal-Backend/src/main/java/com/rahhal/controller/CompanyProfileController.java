package com.rahhal.controller;

import com.rahhal.dto.CompanyProfileDTO;
import com.rahhal.service.CompanyProfileService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/company-profiles")
public class CompanyProfileController {

    private final CompanyProfileService companyProfileService;

    public CompanyProfileController(CompanyProfileService companyProfileService) {
        this.companyProfileService = companyProfileService;
    }

    @GetMapping("/{companyName}")
    public ResponseEntity<CompanyProfileDTO> getProfileByName(@PathVariable String companyName) {
        CompanyProfileDTO profile = companyProfileService.getCompanyProfile(companyName);
        return ResponseEntity.ok(profile);
    }
}

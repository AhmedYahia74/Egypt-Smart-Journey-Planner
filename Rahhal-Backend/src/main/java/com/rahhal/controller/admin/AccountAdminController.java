package com.rahhal.controller.admin;

import com.rahhal.dto.CompanyDto;
import com.rahhal.dto.UserDto;
import com.rahhal.service.AdminService;
import com.stripe.exception.StripeException;
import com.stripe.model.AccountLink;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.List;
@Slf4j
@RestController
@RequestMapping("/api/admin/accounts")
@PreAuthorize("hasRole('ROLE_ADMIN')")
public class AccountAdminController {

    private final AdminService adminService;

    public AccountAdminController(AdminService adminServiceService) {this.adminService = adminServiceService;}

    @Tag(name = "Account Management - Admin side")
    @Operation(summary = "Add a new company",
            description = "Allows an admin to add a new company.<br><br>" +
                    "returns a 201 status code if the company is added successfully.")
    @PostMapping("/company")
    public void addNewCompany(@Valid @RequestBody CompanyDto company,
                                              HttpServletResponse response) throws IOException, StripeException {
        AccountLink accountLink = adminService.addNewCompany(company);
        log.info("Redirecting to Stripe account onboarding for company: {}", company.getName());
        log.info("Account Link URL: {}", accountLink.getUrl());
        response.sendRedirect(accountLink.getUrl());
    }

    @GetMapping
    public ResponseEntity<List<UserDto>> viewAllAccounts()
    {
        List<UserDto> accounts=adminService.viewAllAccounts();
        return ResponseEntity.ok(accounts);
    }

    @DeleteMapping("/{userId}")
    public ResponseEntity<Void> deleteAccount( @Valid @PathVariable int userId) throws StripeException {
        adminService.deleteAccount(userId);
        return ResponseEntity.ok().build();
    }

    @PutMapping("/company/{companyId}")
    public ResponseEntity<Void> reactivateCompany( @Valid @PathVariable int companyId) {
        adminService.reactivateCompanyAccount(companyId);
        return ResponseEntity.ok().build();
    }

    @PutMapping("/status")
    public ResponseEntity<Void> changeStatus( @Valid @RequestParam("userId") int userId,
                                              @RequestParam("status") boolean status) {
        adminService.changeAccountStatus(userId, status);
        return ResponseEntity.ok().build();
    }



}

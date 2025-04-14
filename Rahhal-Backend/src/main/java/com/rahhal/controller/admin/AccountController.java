package com.rahhal.controller.admin;

import com.rahhal.dto.CompanyDto;
import com.rahhal.service.AdminService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/admin/accounts")
@PreAuthorize("hasRole('ROLE_ADMIN')")
public class AccountController {

    private final AdminService adminService;

    public AccountController(AdminService adminServiceService) {this.adminService = adminServiceService;}

    @PostMapping("/company")
    public ResponseEntity<Void> addNewCompany(@Valid @RequestBody CompanyDto company) {
        adminService.addNewCompany(company);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }
}

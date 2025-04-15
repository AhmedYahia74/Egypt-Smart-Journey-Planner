package com.rahhal.controller.admin;

import com.rahhal.dto.CompanyDto;
import com.rahhal.dto.UserDto;
import com.rahhal.service.AdminService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

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

    @GetMapping
    public ResponseEntity<List<UserDto>> viweAllAccounts()
    {
        List<UserDto> accounts=adminService.viewAllAccounts();
        return ResponseEntity.ok(accounts);
    }

    @DeleteMapping("/{userId}")
    public ResponseEntity<Void> deleteAccount(@PathVariable int userId)
    {
        adminService.deleteAccount(userId);
        return ResponseEntity.noContent().build();
    }

}

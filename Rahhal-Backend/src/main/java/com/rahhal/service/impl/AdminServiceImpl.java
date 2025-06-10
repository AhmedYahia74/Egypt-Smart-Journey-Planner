package com.rahhal.service.impl;

import com.rahhal.dto.CompanyDto;
import com.rahhal.dto.UserDto;
import com.rahhal.entity.Company;
import com.rahhal.entity.CompanyProfile;
import com.rahhal.entity.User;
import com.rahhal.exception.EntityAlreadyExistsException;
import com.rahhal.exception.EntityNotFoundException;
import com.rahhal.mapper.CompanyMapper;
import com.rahhal.mapper.CompanyProfileMapper;
import com.rahhal.mapper.UserMapper;
import com.rahhal.repository.CompanyProfileRepository;
import com.rahhal.repository.CompanyRepository;
import com.rahhal.repository.UserRepository;
import com.rahhal.service.AdminService;
import com.rahhal.service.StripeService;
import com.stripe.exception.StripeException;
import com.stripe.model.AccountLink;
import com.stripe.param.AccountLinkCreateParams;
import lombok.AllArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@AllArgsConstructor
public class AdminServiceImpl implements AdminService {

   private final CompanyRepository companyRepository;
   private final CompanyMapper companyMapper;
   private final UserRepository userRepository;
   private final UserMapper userMapper;
   private final CompanyProfileRepository companyProfileRepository;
   private final CompanyProfileMapper companyProfileMapper;
   private final StripeService stripeService;
   private final PasswordEncoder passwordEncoder;

    @Override
    public AccountLink addNewCompany(CompanyDto companyDto) throws StripeException {


        Company company = companyMapper.mapToEntity(companyDto);

        userRepository.findByEmail(company.getEmail())
                .ifPresent(user ->
                {
                    throw new EntityAlreadyExistsException("User with email " + user.getEmail() + " already exists");
                });

        if (companyRepository.existsByName(company.getName()))
            throw new EntityAlreadyExistsException("Company with name " + company.getName() + " already exists");

        company.setPassword(passwordEncoder.encode(company.getPassword()));
        companyRepository.save(company);

        // Create Stripe account for the company
        AccountLinkCreateParams accountLinkCreateParams = stripeService.createCompanyAccount(company.getEmail());

        // Save the Stripe account ID in the CompanyDto
        companyDto.setStripeAccountId(accountLinkCreateParams.getAccount());
        CompanyProfile companyProfile = companyProfileMapper.mapToEntity(companyDto, company);
        companyProfileRepository.save(companyProfile);

        return AccountLink.create(accountLinkCreateParams);

    }

    @Override
    public void deleteAccount(int id) throws StripeException {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Account not found"));

        if (user instanceof Company) {
            CompanyProfile companyProfile = companyProfileRepository.findByCompany((Company) user);

            stripeService.deleteAccount(companyProfile.getStripeAccountId());

            companyProfileRepository.delete(companyProfile);

        }

        userRepository.delete(user);
    }

    @Override
    public List<UserDto> viewAllAccounts() {
        List<User> users = userRepository.findAll();
        return userMapper.mapToEntity(users);
    }

    @Override
    public void reactivateCompanyAccount(int companyId) {
        Company company = companyRepository.findById(companyId)
                .orElseThrow(() -> new EntityNotFoundException("Company not found"));
        company.setSuspended(false);
    }

    @Override
    public void changeAccountStatus(int userId,boolean status) {
        User user=userRepository.findById(userId)
                .orElseThrow(()-> new EntityNotFoundException("user not found"));

        user.setSuspended(status);
        userRepository.save(user);
    }

}

package com.rahhal.service.Impl;

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
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class AdminServiceImpl implements AdminService {

   private final CompanyRepository companyRepository;
   private final CompanyMapper companyMapper;
   private final UserRepository userRepository;
   private final UserMapper userMapper;
   private final CompanyProfileRepository companyProfileRepository;
   private final CompanyProfileMapper companyProfileMapper;
   private final PasswordEncoder passwordEncoder;


    public AdminServiceImpl(CompanyRepository companyRepository, CompanyMapper companyMapper, UserRepository userRepository, UserMapper userMapper, CompanyProfileRepository companyProfileRepository, CompanyProfileMapper companyProfileMapper, PasswordEncoder passwordEncoder) {
        this.companyRepository = companyRepository;
        this.companyMapper = companyMapper;
        this.userRepository = userRepository;
        this.userMapper = userMapper;
        this.companyProfileRepository = companyProfileRepository;
        this.companyProfileMapper = companyProfileMapper;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public void addNewCompany(CompanyDto companyDto) {


        Company company = companyMapper.mapToEntity(companyDto);

        companyRepository.findByEmail(company.getEmail())
                .ifPresent(user ->
                {
                    throw new EntityAlreadyExistsException("User with email " + user.getEmail() + " already exists");
                });

        if(companyRepository.existsByName(company.getName()))
                    throw new EntityAlreadyExistsException("User with name " + company.getName() + " already exists");


        company.setPassword(passwordEncoder.encode(company.getPassword()));
        companyRepository.save(company);

        CompanyProfile companyProfile = companyProfileMapper.mapToEntity(companyDto,company);

        companyProfileRepository.save(companyProfile);

    }

    @Override
    public void deleteAccount(int id) {
        User user= userRepository.findById(id)
                .orElseThrow(() ->  new  EntityNotFoundException("Account not found"));

        userRepository.delete(user);
    }

    @Override
    public List<UserDto> viewAllAccounts() {
        List<User> users=userRepository.findAll();
        List<UserDto> userDtos= userMapper.mapToEntity(users);
        return userDtos;
    }

    @Override
    public void reactivateCompanyAccount(int companyId) {
        User user=userRepository.findById(companyId)
                .orElseThrow(()-> new EntityNotFoundException("user not found"));

        if(user instanceof Company)
        {
            user.setSuspended(false);
            ((Company) user).setSubscriptionExpireDate(LocalDateTime.now().plusYears(1));
            userRepository.save(user);
        }
        else
            throw new EntityNotFoundException("This account not for company");
    }

    @Override
    public void changeAccountStatus(int userId,boolean status) {
        User user=userRepository.findById(userId)
                .orElseThrow(()-> new EntityNotFoundException("user not found"));

        user.setSuspended(status);
        userRepository.save(user);
    }

}

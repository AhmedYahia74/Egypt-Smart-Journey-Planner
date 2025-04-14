package com.rahhal.service.Impl;

import com.rahhal.dto.CompanyDto;
import com.rahhal.entity.Company;
import com.rahhal.entity.User;
import com.rahhal.exception.EntityAlreadyExistsException;
import com.rahhal.exception.EntityNotFoundException;
import com.rahhal.mapper.CompanyMapper;
import com.rahhal.repository.CompanyRepository;
import com.rahhal.repository.UserRepository;
import com.rahhal.service.AdminService;
import org.springframework.stereotype.Service;

@Service
public class AdminServiceImpl implements AdminService {

   private final CompanyRepository companyRepository;
   private final CompanyMapper companyMapper;
   private final UserRepository userRepository;


    public AdminServiceImpl(CompanyRepository companyRepository, CompanyMapper companyMapper, UserRepository userRepository) {
        this.companyRepository = companyRepository;
        this.companyMapper = companyMapper;
        this.userRepository = userRepository;
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

        companyRepository.save(company);

    }

    @Override
    public void deleteAccount(int id) {
        User user= userRepository.findById(id)
                .orElseThrow(() ->  new  EntityNotFoundException("Account not found"));

        userRepository.delete(user);
    }

}

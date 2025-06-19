package com.rahhal.repository;

import com.rahhal.entity.Company;
import com.rahhal.entity.CompanyProfile;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface CompanyProfileRepository extends JpaRepository<CompanyProfile, Integer> {
    CompanyProfile findByCompany(Company user);

    @Query("SELECT c.stripeAccountId FROM CompanyProfile c WHERE c.company = :company")
    String findStripeAccountIdByCompany(@Param("company") Company company);

    Optional<CompanyProfile> findByName(String name);
}

package com.rahhal.repository;

import com.rahhal.entity.Company;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface CompanyRepository  extends JpaRepository<Company, Integer> {
    Optional<Company> findByEmail(String username);
    boolean existsByName(String name);
}

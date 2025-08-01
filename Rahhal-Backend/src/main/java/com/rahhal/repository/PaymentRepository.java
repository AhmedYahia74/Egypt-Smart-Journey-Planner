package com.rahhal.repository;

import com.rahhal.entity.Payment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PaymentRepository extends JpaRepository<Payment, Integer> {
    boolean existsBySessionId(String sessionId);
}

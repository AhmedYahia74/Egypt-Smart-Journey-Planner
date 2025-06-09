package com.rahhal.service;

public interface EmailService {
    void sendEmail(String toEmail, String subject, String body);
}

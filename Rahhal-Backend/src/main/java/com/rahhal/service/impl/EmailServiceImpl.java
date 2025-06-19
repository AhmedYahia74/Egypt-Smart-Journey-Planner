package com.rahhal.service.impl;

import com.rahhal.service.EmailService;
import com.rahhal.exception.EmailSendingException;
import org.springframework.mail.MailException;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;

@Service
public class EmailServiceImpl implements EmailService {
    private final JavaMailSender mailSender;
    
    public EmailServiceImpl(JavaMailSender mailSender) {
        this.mailSender = mailSender;
    }
    
    @Override
    public void sendEmail(String reciever, String subject, String body) {
        try {
            MimeMessage msg = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(msg, true, "UTF-8");

            helper.setTo(reciever);
            helper.setSubject(subject);
            helper.setText(body, true);

            mailSender.send(msg);
        }
        catch (MailException | MessagingException e) {
            throw new EmailSendingException("Failed to send email to " + reciever + ": " + e.getMessage());
        }
    }
}
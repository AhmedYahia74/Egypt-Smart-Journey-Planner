package com.rahhal.service.Impl;

import com.rahhal.dto.AuthenticationResponseDto;
import com.rahhal.dto.LogInRequestDto;
import com.rahhal.dto.TouristDto;
import com.rahhal.entity.Company;
import com.rahhal.entity.User;
import com.rahhal.exception.AccountIsSuspendedException;
import com.rahhal.exception.EntityAlreadyExistsException;
import com.rahhal.exception.EntityNotFoundException;
import com.rahhal.mapper.TouristMapper;
import com.rahhal.repository.UserRepository;
import com.rahhal.security.JwtService;
import com.rahhal.service.AuthService;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class AuthServiceImpl implements AuthService {
    private final UserRepository userRepository;
    private final TouristMapper touristMapper;
    private final AuthenticationManager authenticationManager;
    private final JwtService jwtService;

    public AuthServiceImpl(UserRepository userRepository, TouristMapper touristMapper, AuthenticationManager authenticationManager, JwtService jwtService) {
        this.userRepository = userRepository;
        this.touristMapper = touristMapper;
        this.authenticationManager = authenticationManager;
        this.jwtService = jwtService;
    }

    @Override
    public void signUp(TouristDto request) {
        userRepository.findByEmail(request.getEmail())
                .ifPresent(user ->
                {
                    throw new EntityAlreadyExistsException("User with email " + user.getEmail() + " already exists");
                });

        userRepository.save(touristMapper.mapToEntity(request));
    }

    @Override
    public AuthenticationResponseDto logIn(LogInRequestDto request) {

        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new EntityNotFoundException("User not found"));


        if (user instanceof Company) {

            if (LocalDateTime.now().isAfter(((Company) user).getSubscriptionExpireDate())) {
                user.setSuspended(true);
                userRepository.save(user);
                throw new AccountIsSuspendedException ("Account suspended subscription expired");
            }
        }

       try {
           authenticationManager.authenticate(
                   new UsernamePasswordAuthenticationToken(request.getEmail(), request.getPassword()));

       }catch (Exception e) {
           user.setFailedLoginAttempts(user.getFailedLoginAttempts() + 1);

           if (user.getFailedLoginAttempts() >3) {
               user.setSuspended(true);
               user.setSuspendedAt(LocalDateTime.now());
               userRepository.save(user);
               throw new AccountIsSuspendedException("The account has been suspended");
           }

           userRepository.save(user);
           throw new EntityNotFoundException("Invalid credentials. Attempt " + user.getFailedLoginAttempts() + 1 + " of 3");
       }

       //***************** Dosn't Work ******************//
        if (user.isSuspended()) {
            if (user.getSuspendedAt() != null) {
                if (LocalDateTime.now().isBefore(user.getSuspendedAt().plusMinutes(2))) {
                    throw new AccountIsSuspendedException("Account is suspended try again at " + 2 + "mins");
                }

                user.setSuspended(false);
                user.setFailedLoginAttempts(0);
                user.setSuspendedAt(null);
                userRepository.save(user);

            }

        }
        /**************************************/

        user.setFailedLoginAttempts(0);
        user.setSuspended(false);
        user.setSuspendedAt(null);
        userRepository.save(user);

        String jwtToken = jwtService.generateToken(user);
        return AuthenticationResponseDto.builder()
                .accessToken(jwtToken)
                .userId(user.getUserId())
                .build();
    }
}
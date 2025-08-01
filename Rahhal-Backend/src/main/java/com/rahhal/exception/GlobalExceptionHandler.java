package com.rahhal.exception;

import com.rahhal.dto.ErrorResponseDTO;
import com.rahhal.enums.ErrorCode;
import com.stripe.exception.StripeException;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.InternalAuthenticationServiceException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Object> handleValidationExceptions(
            MethodArgumentNotValidException ex,
            HttpServletRequest request
    ) {
        log.error("Validation Error: {}", ex.getMessage(), ex);

        Map<String, String> errors = ex.getBindingResult().getAllErrors().stream()
                .collect(Collectors.toMap(
                        error -> ((FieldError) error).getField(),
                        error -> error.getDefaultMessage() != null ? error.getDefaultMessage() : "")
                );

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.VALIDATION_ERROR.getStatus().value())
                .error(ErrorCode.VALIDATION_ERROR.getStatus().getReasonPhrase())
                .message(ErrorCode.VALIDATION_ERROR.getDefaultMessage())
                .path(request.getRequestURI())
                .build();

        Map<String, Object> response = new HashMap<>();
        response.put("error", error);
        response.put("validationErrors", errors);

        return new ResponseEntity<>(response, ErrorCode.VALIDATION_ERROR.getStatus());
    }
    
    @ExceptionHandler(EntityNotFoundException.class)
    public ResponseEntity<ErrorResponseDTO> handleEntityNotFoundException(
            EntityNotFoundException ex,
            HttpServletRequest request
    ) {
        log.error("Entity Not Found Error: {}", ex.getMessage(), ex);

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.USER_NOT_FOUND.getStatus().value())
                .error(ErrorCode.USER_NOT_FOUND.getStatus().getReasonPhrase())
                .message(ex.getMessage())
                .path(request.getRequestURI())
                .build();

        return new ResponseEntity<>(error, ErrorCode.USER_NOT_FOUND.getStatus());
    }
    @ExceptionHandler(StripeException.class)
    public ResponseEntity<ErrorResponseDTO> handleStripeException(
            StripeException ex, HttpServletRequest request) {
        log.error("Stripe Error: {}", ex.getMessage(), ex);

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(HttpStatus.BAD_REQUEST.value()) // 400 Bad Request
                .error(HttpStatus.BAD_REQUEST.getReasonPhrase())
                .message("An error occurred while processing the payment. Please try again later.")
                .path(request.getRequestURI())
                .build();

        return new ResponseEntity<>(error, HttpStatus.BAD_REQUEST);
    }

    @ExceptionHandler(JwtException.class)
    public ResponseEntity<ErrorResponseDTO> handleJwtException(
            JwtException ex, HttpServletRequest request) {
        log.warn("Invalid JWT: {}", ex.getMessage());

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.UNAUTHORIZED.getStatus().value()) // 401 Unauthorized
                .error(ErrorCode.UNAUTHORIZED.getStatus().getReasonPhrase())
                .message("Invalid or expired token. Please log in again.")
                .path(request.getRequestURI())
                .build();

        return new ResponseEntity<>(error, ErrorCode.UNAUTHORIZED.getStatus());
    }

    @ExceptionHandler(InternalAuthenticationServiceException.class)
    public ResponseEntity<ErrorResponseDTO> handleInternalAuthenticationServiceException(
            InternalAuthenticationServiceException ex, HttpServletRequest request) {
        log.error("Internal Authentication Service Error: {}", ex.getMessage(), ex);

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.UNAUTHORIZED.getStatus().value()) // 401 Unauthorized
                .error(ErrorCode.UNAUTHORIZED.getStatus().getReasonPhrase())
                .message("Invalid email or password.")
                .path(request.getRequestURI())
                .build();

        return new ResponseEntity<>(error, ErrorCode.UNAUTHORIZED.getStatus());
    }
    @ExceptionHandler(AuthenticationException .class)
    public ResponseEntity<ErrorResponseDTO> handleAuthenticationException(
            AuthenticationException ex, HttpServletRequest request) {
        log.error("Username Not Found: {}", ex.getMessage(), ex);
        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.UNAUTHORIZED.getStatus().value()) // 401 Unauthorized
                .error(ErrorCode.UNAUTHORIZED.getStatus().getReasonPhrase())
                .message("Invalid email or password.")
                .path(request.getRequestURI())
                .build();

        return new ResponseEntity<>(error, ErrorCode.UNAUTHORIZED.getStatus());
    }


    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ErrorResponseDTO> handleAccessDeniedException(
            AccessDeniedException ex, HttpServletRequest request) {
        log.warn("Access Denied: {}", ex.getMessage());

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.ACCESS_DENIED.getStatus().value()) // 403 Forbidden
                .error(ErrorCode.ACCESS_DENIED.getStatus().getReasonPhrase())
//                .message("You do not have permission to access this resource.")
                .message(ex.getMessage())
                .path(request.getRequestURI())
                .build();

        return new ResponseEntity<>(error, ErrorCode.ACCESS_DENIED.getStatus());
    }

    @ExceptionHandler(EntityAlreadyExistsException.class)
    public ResponseEntity<Object> handleEntityAlreadyExistsException(
            EntityAlreadyExistsException ex,
            HttpServletRequest request
    ) {
        log.error("Entity Already Exists: {}", ex.getMessage(), ex);

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.USER_ALREADY_EXISTS.getStatus().value()) // Use 409 Conflict
                .error(ErrorCode.USER_ALREADY_EXISTS.getStatus().getReasonPhrase())
                .message(ex.getMessage())
                .path(request.getRequestURI())
                .build();

        return new ResponseEntity<>(error, ErrorCode.USER_ALREADY_EXISTS.getStatus());
    }

    @ExceptionHandler(TripModificationNotAllowedException.class)
    public ResponseEntity<ErrorResponseDTO> handleTripModificationNotAllowedException(
            TripModificationNotAllowedException ex, HttpServletRequest request) {

        log.error("Trip Modification Not Allowed: {}", ex.getMessage(), ex);

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.ACCESS_DENIED.getStatus().value())
                .error(ErrorCode.ACCESS_DENIED.getStatus().getReasonPhrase())
                .message(ex.getMessage())
                .path(request.getRequestURI())
                .build();

        return ResponseEntity.status(ErrorCode.ACCESS_DENIED.getStatus()).body(error);
    }

    @ExceptionHandler(CompanyHasNoInactiveTripsExeption.class)
    public ResponseEntity<ErrorResponseDTO>handelCompanyHasNoInactiveTripsExeption(
            CompanyHasNoInactiveTripsExeption ex,HttpServletRequest request)
    {
        log.error("Company Has No Inactive Trips: {}",ex.getMessage(),ex);

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.COMPANY_HAS_NO_INACTIVE_TRIPS.getStatus().value())
                .error(ErrorCode.COMPANY_HAS_NO_INACTIVE_TRIPS.getStatus().getReasonPhrase())
                .message(ex.getMessage())
                .path(request.getRequestURI())
                .build();

        return ResponseEntity.status(ErrorCode.COMPANY_HAS_NO_INACTIVE_TRIPS.getStatus()).body(error);

    }



    @ExceptionHandler(TripAlreadyActivatedException.class)
    public ResponseEntity<ErrorResponseDTO>handelTripAlreadyActivatedException(
            TripAlreadyActivatedException ex,HttpServletRequest request)
    {
        log.error("Trip Has Been Already Activated: {}",ex.getMessage(),ex);

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.TRIP_ALREADY_ACTIVATED.getStatus().value())
                .error(ErrorCode.TRIP_ALREADY_ACTIVATED.getStatus().getReasonPhrase())
                .message(ex.getMessage())
                .path(request.getRequestURI())
                .build();

        return ResponseEntity.status(ErrorCode.TRIP_ALREADY_ACTIVATED.getStatus()).body(error);

    }

    @ExceptionHandler(EmailSendingException.class)
    public ResponseEntity<ErrorResponseDTO> handleEmailSendingException(
            EmailSendingException ex, HttpServletRequest request) {
        log.error("Email Sending Error: {}", ex.getMessage(), ex);

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.EMAIL_SENDING_ERROR.getStatus().value())
                .error(ErrorCode.EMAIL_SENDING_ERROR.getStatus().getReasonPhrase())
                .message(ex.getMessage())
                .path(request.getRequestURI())
                .build();

        return new ResponseEntity<>(error, ErrorCode.EMAIL_SENDING_ERROR.getStatus());
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponseDTO> handleGlobalException(
            Exception ex, HttpServletRequest request) {
        log.error("Unexpected Error: {}", ex.getMessage(), ex);

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.INTERNAL_SERVER_ERROR.getStatus().value())
                .error(ErrorCode.INTERNAL_SERVER_ERROR.getStatus().getReasonPhrase())
                .message("An unexpected error occurred. Please try again later.")
                .path(request.getRequestURI())
                .build();

        return new ResponseEntity<>(error, ErrorCode.INTERNAL_SERVER_ERROR.getStatus());
    }

}

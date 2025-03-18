package com.rahhal.exception;

import com.rahhal.dto.ErrorResponseDTO;
import com.rahhal.enums.ErrorCode;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
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


    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ErrorResponseDTO> handleAccessDeniedException(
            AccessDeniedException ex, HttpServletRequest request) {
        log.warn("Access Denied: {}", ex.getMessage());

        ErrorResponseDTO error = ErrorResponseDTO.builder()
                .timestamp(LocalDateTime.now())
                .status(ErrorCode.ACCESS_DENIED.getStatus().value()) // 403 Forbidden
                .error(ErrorCode.ACCESS_DENIED.getStatus().getReasonPhrase())
                .message("You do not have permission to access this resource.")
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
}

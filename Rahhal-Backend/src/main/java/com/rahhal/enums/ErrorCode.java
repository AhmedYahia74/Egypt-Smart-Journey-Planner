package com.rahhal.enums;

import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
public enum ErrorCode {

    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "User not found"),
    USER_ALREADY_EXISTS(HttpStatus.CONFLICT, "USER already exists"),

    VALIDATION_ERROR(HttpStatus.BAD_REQUEST, "Validation failed"),

    INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "An unexpected error occurred"),
    ACCESS_DENIED(HttpStatus.FORBIDDEN, "You hasn't access to this page" ),
    UNAUTHORIZED(HttpStatus.UNAUTHORIZED,"UNAUTHORIZED" ),
    COMPANY_HAS_NO_INACTIVE_TRIPS(HttpStatus.NOT_FOUND,"There is no inactive trip"),
    TRIP_ALREADY_ACTIVATED(HttpStatus.CONFLICT,"Trip is already activated"),
    EMAIL_SENDING_ERROR(HttpStatus.BAD_GATEWAY, "Failed to send email"),
    Invalid_TripDate_Exception(HttpStatus.BAD_REQUEST,"Invalid Trip Date");
    private final HttpStatus status;
    private final String defaultMessage;

    ErrorCode(HttpStatus status, String defaultMessage) {
        this.status = status;
        this.defaultMessage = defaultMessage;
    }

}
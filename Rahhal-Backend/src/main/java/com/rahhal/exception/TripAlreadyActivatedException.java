package com.rahhal.exception;

public class TripAlreadyActivatedException extends RuntimeException {
    public TripAlreadyActivatedException(String message) {
        super(message);
    }
}

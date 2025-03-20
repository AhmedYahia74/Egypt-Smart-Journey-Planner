package com.rahhal.exception;

public class TripModificationNotAllowedException extends RuntimeException{
    public TripModificationNotAllowedException(String message) {
        super(message);
    }
}

package com.rahhal.exception;

public class CompanyHasNoInactiveTripsExeption extends RuntimeException {
    public CompanyHasNoInactiveTripsExeption(String message) {
        super(message);
    }
}

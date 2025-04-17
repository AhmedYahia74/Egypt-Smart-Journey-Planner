package com.rahhal.exception;

public class AccountIsSuspendedException extends RuntimeException {
    public AccountIsSuspendedException(String message) {
        super(message);
    }
}

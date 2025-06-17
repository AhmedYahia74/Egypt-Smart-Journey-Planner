package com.rahhal.security;

import lombok.Getter;

import java.security.Principal;

public class StompPrincipal implements Principal {

    private final String name;
    @Getter
    private final int id;


    public StompPrincipal(String name, int id) {
        this.name = name;
        this.id = id;
    }

    @Override
    public String getName() {
        return name;
    }
}

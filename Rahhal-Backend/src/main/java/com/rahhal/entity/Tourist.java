package com.rahhal.entity;

import jakarta.persistence.DiscriminatorValue;
import jakarta.persistence.Entity;
import lombok.*;

@Entity
@DiscriminatorValue("TOURIST")
public class Tourist extends User{

}

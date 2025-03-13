package com.rahhal.entity;

import com.rahhal.enums.UserRole;
import jakarta.persistence.*;
import lombok.*;
import jakarta.validation.constraints.*;


@Entity
@Table(name = "users")
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@ToString
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int userId;

    @Email(message = "Please provide a valid e-mail")
    @NotNull
    @Column(unique = true)
    private String email;

    @NotNull
    @Size(min = 2, message = "password must be at least 2 characters long")
    private String password;

    @NotNull
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private UserRole role;
}

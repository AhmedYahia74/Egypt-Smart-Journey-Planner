package com.rahhal.mapper;


import com.rahhal.dto.UserDto;
import com.rahhal.entity.User;
import jakarta.persistence.DiscriminatorValue;
import org.springframework.stereotype.Component;
import java.util.List;
import java.util.stream.Collectors;

@Component
public class UserMapper {
    public List<UserDto> mapToEntity(List<User> users)
    {

        List<UserDto> userDtos= users.stream()
                .map(user -> UserDto.builder()
                        .userId(user.getUserId())
                        .name(user.getName())
                        .email(user.getEmail())
                        .role(user.getClass().getAnnotation(DiscriminatorValue.class).value())
                        .suspended(user.isSuspended())
                        .build())
                .collect(Collectors.toList());

        return userDtos;
    }

}

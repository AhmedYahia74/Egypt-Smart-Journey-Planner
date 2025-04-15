package com.rahhal.mapper;


import com.rahhal.dto.UserDto;
import com.rahhal.entity.User;
import jakarta.persistence.DiscriminatorValue;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Component
public class UserMapper {
    public List<UserDto> mapToEntity(List<User> users)
    {
        List<UserDto> userDtos=new ArrayList<>();
        for(User user:users)
        {
            UserDto userDto=UserDto.builder()
                    .userId(user.getUserId())
                    .name(user.getName())
                    .email(user.getEmail())
                    .role(user.getClass().getAnnotation(DiscriminatorValue.class).value())
                    .build();
            userDtos.add(userDto);
        }
        return userDtos;
    }

}

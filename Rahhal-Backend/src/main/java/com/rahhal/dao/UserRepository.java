package com.rahhal.dao;

import com.rahhal.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository  extends JpaRepository <User,Integer>{

}

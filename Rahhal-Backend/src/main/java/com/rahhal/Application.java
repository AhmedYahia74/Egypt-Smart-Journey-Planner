package com.rahhal;

import com.rahhal.entity.User;
import com.rahhal.repository.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class Application {

	public static void main(String[] args) {
		SpringApplication.run(Application.class, args);
	}

	@Bean
	public CommandLineRunner commandLineRunner(UserRepository userRepository) {
		return args -> {
			// test
//			userRepository.save(new User(0,"test2@gmail", "1234", "tourist"));
//			System.out.println("User saved");
			userRepository.delete(userRepository.findById(1).get());
			System.out.println("User deleted");
		};
	}
}

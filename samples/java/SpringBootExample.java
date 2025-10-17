/**
 * Sample Spring Boot application demonstrating enterprise Java debugging scenarios
 * for ChatDBG JDB integration testing.
 */

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import java.util.List;
import java.util.ArrayList;
import java.util.Optional;

@SpringBootApplication
@RestController
@RequestMapping("/api")
public class SpringBootExample {

    @Autowired
    private UserService userService;

    @GetMapping("/users/{id}")
    public User getUser(@PathVariable Long id) {
        // This could cause null pointer if userService is not properly injected
        return userService.getUserById(id);
    }

    @PostMapping("/users")
    public User createUser(@RequestBody User user) {
        if (user == null) {
            throw new IllegalArgumentException("User cannot be null");
        }

        if (user.getName() == null || user.getName().trim().isEmpty()) {
            throw new IllegalArgumentException("User name cannot be null or empty");
        }

        return userService.saveUser(user);
    }

    @GetMapping("/users")
    public List<User> getAllUsers() {
        return userService.getAllUsers();
    }

    public static void main(String[] args) {
        SpringApplication.run(SpringBootExample.class, args);
    }
}

class User {
    private Long id;
    private String name;
    private String email;
    private List<String> roles;

    // Constructors
    public User() {}

    public User(String name, String email) {
        this.name = name;
        this.email = email;
        this.roles = new ArrayList<>();
    }

    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public List<String> getRoles() { return roles; }
    public void setRoles(List<String> roles) { this.roles = roles; }

    @Override
    public String toString() {
        return "User{" +
                "id=" + id +
                ", name='" + name + '\'' +
                ", email='" + email + '\'' +
                '}';
    }
}

class UserService {
    private List<User> users = new ArrayList<>();

    public User getUserById(Long id) {
        if (id == null) {
            return null; // This could cause null pointer in controller
        }

        Optional<User> user = users.stream()
                .filter(u -> id.equals(u.getId()))
                .findFirst();

        return user.orElse(null); // Could return null
    }

    public User saveUser(User user) {
        if (user == null) {
            throw new IllegalArgumentException("User cannot be null");
        }

        // Generate ID if not present
        if (user.getId() == null) {
            user.setId(System.currentTimeMillis());
        }

        users.add(user);
        return user;
    }

    public List<User> getAllUsers() {
        return new ArrayList<>(users); // Return defensive copy
    }

    public void deleteUser(Long id) {
        if (id == null) {
            throw new IllegalArgumentException("ID cannot be null");
        }

        users.removeIf(user -> id.equals(user.getId()));
    }
}
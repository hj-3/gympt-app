package com.gympt.backend.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.*;

@Slf4j
@RestController
@RequestMapping("/api/v1/routines")
@RequiredArgsConstructor
public class WorkoutRoutineController {

    @GetMapping("/today/{userId}")
    public ResponseEntity<Map<String, Object>> getTodayRoutine(
            @PathVariable String userId,
            @AuthenticationPrincipal UserDetails userDetails) {

        log.info("Get today routine for user: {}", userId);

        // TODO: Implement actual routine logic
        // For now, return a default routine
        Map<String, Object> routine = new HashMap<>();
        routine.put("routineId", UUID.randomUUID().toString());
        routine.put("userId", userId);
        routine.put("date", LocalDate.now().toString());
        routine.put("exercises", Arrays.asList(
                createExercise("Push-up", 3, 12),
                createExercise("Squat", 3, 15),
                createExercise("Plank", 3, 30)
        ));

        return ResponseEntity.ok(routine);
    }

    @GetMapping("/{userId}")
    public ResponseEntity<Map<String, Object>> getRoutines(
            @PathVariable String userId,
            @AuthenticationPrincipal UserDetails userDetails) {

        log.info("Get routines for user: {}", userId);

        Map<String, Object> response = new HashMap<>();
        response.put("routines", Collections.emptyList());
        response.put("total", 0);

        return ResponseEntity.ok(response);
    }

    private Map<String, Object> createExercise(String name, int sets, int reps) {
        Map<String, Object> exercise = new HashMap<>();
        exercise.put("name", name);
        exercise.put("sets", sets);
        exercise.put("reps", reps);
        return exercise;
    }
}

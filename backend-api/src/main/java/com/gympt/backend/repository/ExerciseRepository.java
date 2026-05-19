package com.gympt.backend.repository;

import com.gympt.backend.domain.Exercise;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ExerciseRepository extends JpaRepository<Exercise, UUID> {

    List<Exercise> findByCategory(Exercise.ExerciseCategory category);

    List<Exercise> findByDifficulty(Exercise.Difficulty difficulty);

    List<Exercise> findByCategoryAndDifficulty(
        Exercise.ExerciseCategory category,
        Exercise.Difficulty difficulty
    );
}

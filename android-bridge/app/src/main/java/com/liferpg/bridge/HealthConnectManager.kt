package com.liferpg.bridge

import android.content.Context
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.DistanceRecord
import androidx.health.connect.client.records.ExerciseSessionRecord
import androidx.health.connect.client.records.StepsRecord
import androidx.health.connect.client.records.TotalCaloriesBurnedRecord
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import java.time.Instant
import java.time.temporal.ChronoUnit

/**
 * HealthConnectManager handles permission checks and activity ingestion from
 * Google Health Connect on Android (replacing deprecated Google Fit REST APIs).
 */
class HealthConnectManager(private val context: Context) {

    private val healthConnectClient by lazy {
        if (HealthConnectClient.getSdkStatus(context) == HealthConnectClient.SDK_AVAILABLE) {
            HealthConnectClient.getOrCreate(context)
        } else {
            null
        }
    }

    val requiredPermissions = setOf(
        HealthPermission.getReadPermission(StepsRecord::class),
        HealthPermission.getReadPermission(ExerciseSessionRecord::class),
        HealthPermission.getReadPermission(DistanceRecord::class),
        HealthPermission.getReadPermission(TotalCaloriesBurnedRecord::class)
    )

    fun isHealthConnectAvailable(): Boolean {
        return HealthConnectClient.getSdkStatus(context) == HealthConnectClient.SDK_AVAILABLE
    }

    suspend fun hasAllPermissions(): Boolean {
        val client = healthConnectClient ?: return false
        val granted = client.permissionController.getGrantedPermissions()
        return granted.containsAll(requiredPermissions)
    }

    /**
     * Reads exercise sessions and step counts within the specified lookback window.
     */
    suspend fun readActivityData(lookbackHours: Long = 24): HealthConnectBatchData {
        val client = healthConnectClient ?: return HealthConnectBatchData(emptyList(), 0)
        val now = Instant.now()
        val start = now.minus(lookbackHours, ChronoUnit.HOURS)
        val timeFilter = TimeRangeFilter.between(start, now)

        // 1. Read Exercise Sessions
        val exerciseResponse = client.readRecords(
            ReadRecordsRequest(
                recordType = ExerciseSessionRecord::class,
                timeRangeFilter = timeFilter
            )
        )

        val sessions = exerciseResponse.records.map { session ->
            val durationMinutes = ChronoUnit.MINUTES.between(session.startTime, session.endTime).toInt().coerceAtLeast(1)
            val exerciseType = session.exerciseType.toString().lowercase()
                .replace("exercise_type_", "")
                .replace("_", " ")

            HealthConnectSessionData(
                id = session.metadata.id,
                title = session.title ?: "${exerciseType.replaceFirstChar { it.uppercase() }} Workout",
                exerciseType = exerciseType,
                startTime = session.startTime.toString(),
                endTime = session.endTime.toString(),
                durationMinutes = durationMinutes,
                sourceApp = session.metadata.dataOrigin.packageName
            )
        }

        // 2. Read Step Records
        val stepsResponse = client.readRecords(
            ReadRecordsRequest(
                recordType = StepsRecord::class,
                timeRangeFilter = timeFilter
            )
        )
        val totalSteps = stepsResponse.records.sumOf { it.count }

        return HealthConnectBatchData(
            sessions = sessions,
            dailySteps = totalSteps.toInt(),
            date = now.toString()
        )
    }
}

data class HealthConnectSessionData(
    val id: String,
    val title: String,
    val exerciseType: String,
    val startTime: String,
    val endTime: String,
    val durationMinutes: Int,
    val steps: Int? = null,
    val calories: Int? = null,
    val distanceMeters: Double? = null,
    val sourceApp: String? = "Health Connect"
)

data class HealthConnectBatchData(
    val sessions: List<HealthConnectSessionData>,
    val dailySteps: Int,
    val date: String = Instant.now().toString(),
    val deviceName: String = android.os.Build.MODEL ?: "Android Device"
)

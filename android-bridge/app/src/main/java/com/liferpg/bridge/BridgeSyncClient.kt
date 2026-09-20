package com.liferpg.bridge

import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

/**
 * BridgeSyncClient delivers verified Health Connect activity data
 * securely to the LIFE RPG backend server.
 */
class BridgeSyncClient(
    private val serverUrl: String,
    private val pairingToken: String
) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS)
        .build()

    private val gson = Gson()
    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    suspend fun syncBatch(batch: HealthConnectBatchData): Result<String> = withContext(Dispatchers.IO) {
        try {
            val endpoint = serverUrl.trimEnd('/') + "/api/integrations/fitness/health-connect/sync"
            val jsonPayload = gson.toJson(batch)

            val request = Request.Builder()
                .url(endpoint)
                .addHeader("Authorization", "Bearer $pairingToken")
                .addHeader("Content-Type", "application/json")
                .post(jsonPayload.toRequestBody(jsonMediaType))
                .build()

            client.newCall(request).execute().use { response ->
                val body = response.body?.string() ?: ""
                if (response.isSuccessful) {
                    Result.success(body)
                } else {
                    Result.failure(Exception("Sync failed: HTTP ${response.code} - $body"))
                }
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

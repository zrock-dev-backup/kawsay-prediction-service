package utils

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"os"
	"testing"
	"time"
)

func getBaseURL() string {
	if baseURL := os.Getenv("BASE_URL"); baseURL != "" {
		return baseURL
	}
	return "http://localhost:8000"
}

var client = &http.Client{Timeout: 10 * time.Second}

func MakeRequest(t *testing.T, method, urlPath string, body interface{}) (*http.Response, []byte) {
	t.Helper()
	var reqBody io.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			t.Fatalf("Failed to marshal request body: %v", err)
		}
		reqBody = bytes.NewBuffer(jsonBody)
	}

	req, err := http.NewRequest(method, getBaseURL()+urlPath, reqBody)
	if err != nil {
		t.Fatalf("Failed to create request: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("Failed to execute request: %v", err)
	}

	respBodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Logf("Failed to read response body: %v", err) // Log instead of Fatal for some cases
	}
	err = resp.Body.Close()
	if err != nil {
		t.Logf("Failed to read response body: %v", err)
		return nil, nil
	}

	return resp, respBodyBytes
}

func AssertStatusCode(t *testing.T, resp *http.Response, expectedStatus int, bodyBytes []byte) {
	t.Helper()
	if resp.StatusCode != expectedStatus {
		t.Fatalf("Expected status code %d, got %d. Path: %s\nResponse body: %s",
			expectedStatus, resp.StatusCode, resp.Request.URL.Path, string(bodyBytes))
	}
}

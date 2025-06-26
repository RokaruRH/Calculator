package main

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"time"
)

// Структуры для LemonSqueezy API
type LemonSqueezyConfig struct {
	APIKey        string `json:"api_key"`
	StoreID       string `json:"store_id"`
	ProductID     string `json:"product_id"`
	WebhookSecret string `json:"webhook_secret"`
}

type LemonSqueezyOrder struct {
	ID         string `json:"id"`
	Type       string `json:"type"`
	Attributes struct {
		StoreID          int    `json:"store_id"`
		CustomerID       int    `json:"customer_id"`
		Identifier       string `json:"identifier"`
		OrderNumber      int    `json:"order_number"`
		UserName         string `json:"user_name"`
		UserEmail        string `json:"user_email"`
		Currency         string `json:"currency"`
		CurrencyRate     string `json:"currency_rate"`
		Subtotal         int    `json:"subtotal"`
		DiscountTotal    int    `json:"discount_total"`
		Tax              int    `json:"tax"`
		Total            int    `json:"total"`
		SubtotalUSD      int    `json:"subtotal_usd"`
		DiscountTotalUSD int    `json:"discount_total_usd"`
		TaxUSD           int    `json:"tax_usd"`
		TotalUSD         int    `json:"total_usd"`
		TaxName          string `json:"tax_name"`
		TaxRate          string `json:"tax_rate"`
		Status           string `json:"status"`
		StatusFormatted  string `json:"status_formatted"`
		Refunded         bool   `json:"refunded"`
		RefundedAt       string `json:"refunded_at"`
		OrderItems       []struct {
			ID          int    `json:"id"`
			OrderID     int    `json:"order_id"`
			ProductID   int    `json:"product_id"`
			VariantID   int    `json:"variant_id"`
			ProductName string `json:"product_name"`
			VariantName string `json:"variant_name"`
			Price       int    `json:"price"`
			Quantity    int    `json:"quantity"`
		} `json:"order_items"`
		CustomData map[string]any `json:"custom_data"`
		CreatedAt  string         `json:"created_at"`
		UpdatedAt  string         `json:"updated_at"`
	} `json:"attributes"`
}

type LemonSqueezyWebhook struct {
	Meta struct {
		EventName  string         `json:"event_name"`
		CustomData map[string]any `json:"custom_data"`
	} `json:"meta"`
	Data LemonSqueezyOrder `json:"data"`
}

type PremiumUser struct {
	UserID       int64     `json:"user_id"`
	OrderID      string    `json:"order_id"`
	Email        string    `json:"email"`
	PurchaseDate time.Time `json:"purchase_date"`
	IsActive     bool      `json:"is_active"`
}

var (
	lemonSqueezyConfig = LemonSqueezyConfig{
		APIKey:        os.Getenv("LEMONSQUEEZY_API_KEY"),
		StoreID:       os.Getenv("LEMONSQUEEZY_STORE_ID"),
		ProductID:     os.Getenv("LEMONSQUEEZY_PRODUCT_ID"),
		WebhookSecret: os.Getenv("LEMONSQUEEZY_WEBHOOK_SECRET"),
	}
	premiumUsers = make(map[int64]*PremiumUser)
)

// Проверка Premium статуса пользователя
func isPremiumUser(userID int64) bool {
	user, exists := premiumUsers[userID]
	return exists && user.IsActive
}

// Создание checkout URL для покупки Premium
func createCheckoutURL(userID int64) (string, error) {
	baseURL := "https://api.lemonsqueezy.com/v1/checkouts"

	// Подготавливаем данные для создания checkout
	checkoutData := map[string]any{
		"data": map[string]any{
			"type": "checkouts",
			"attributes": map[string]any{
				"product_options": map[string]any{
					"name":        "Rust Raid Calculator Premium",
					"description": "Premium version with advanced features",
				},
				"checkout_data": map[string]any{
					"custom": map[string]any{
						"user_id": userID,
					},
				},
			},
			"relationships": map[string]any{
				"store": map[string]any{
					"data": map[string]any{
						"type": "stores",
						"id":   lemonSqueezyConfig.StoreID, // Исправлено: использовать реальный ID магазина
					},
				},
				"variant": map[string]any{
					"data": map[string]any{
						"type": "variants",
						"id":   lemonSqueezyConfig.ProductID, // Исправлено: использовать реальный ID продукта
					},
				},
			},
		},
	}

	jsonData, err := json.Marshal(checkoutData)
	if err != nil {
		return "", fmt.Errorf("error marshaling checkout data: %v", err)
	}

	req, err := http.NewRequest("POST", baseURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("error creating request: %v", err)
	}

	req.Header.Set("Content-Type", "application/vnd.api+json")
	req.Header.Set("Accept", "application/vnd.api+json")
	req.Header.Set("Authorization", "Bearer "+lemonSqueezyConfig.APIKey)

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("error making request: %v", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("error reading response: %v", err)
	}

	if resp.StatusCode != http.StatusCreated {
		return "", fmt.Errorf("API error: %d - %s", resp.StatusCode, string(body))
	}

	var response struct {
		Data struct {
			Attributes struct {
				URL string `json:"url"`
			} `json:"attributes"`
		} `json:"data"`
	}

	if err := json.Unmarshal(body, &response); err != nil {
		return "", fmt.Errorf("error parsing response: %v", err)
	}

	return response.Data.Attributes.URL, nil
}

// Обработка webhook от LemonSqueezy
func handleLemonSqueezyWebhook(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Error reading body", http.StatusBadRequest)
		return
	}

	// Проверка подписи webhook
	if !validateWebhookSignature(body, r.Header.Get("X-Signature")) {
		http.Error(w, "Invalid signature", http.StatusUnauthorized)
		return
	}

	var webhook LemonSqueezyWebhook
	if err := json.Unmarshal(body, &webhook); err != nil {
		http.Error(w, "Error parsing webhook", http.StatusBadRequest)
		return
	}

	// Обработка события покупки
	switch webhook.Meta.EventName {
	case "order_created":
		handleOrderCreated(webhook)
	case "order_refunded":
		handleOrderRefunded(webhook)
	default:
		fmt.Printf("Unhandled webhook event: %s\n", webhook.Meta.EventName)
	}

	w.WriteHeader(http.StatusOK)
}

// Проверка подписи webhook
func validateWebhookSignature(body []byte, signature string) bool {
	if lemonSqueezyConfig.WebhookSecret == "" {
		return false
	}

	mac := hmac.New(sha256.New, []byte(lemonSqueezyConfig.WebhookSecret))
	mac.Write(body)
	expectedSignature := hex.EncodeToString(mac.Sum(nil))

	return hmac.Equal([]byte(signature), []byte(expectedSignature))
}

// Обработка создания заказа
func handleOrderCreated(webhook LemonSqueezyWebhook) {
	// Извлекаем user_id из custom_data
	userIDInterface, ok := webhook.Data.Attributes.CustomData["user_id"]
	if !ok {
		fmt.Println("No user_id in custom_data")
		return
	}

	var userID int64
	switch v := userIDInterface.(type) {
	case float64:
		userID = int64(v)
	case string:
		parsed, err := strconv.ParseInt(v, 10, 64)
		if err != nil {
			fmt.Printf("Error parsing user_id: %v\n", err)
			return
		}
		userID = parsed
	default:
		fmt.Printf("Invalid user_id type: %T\n", v)
		return
	}

	// Создаем Premium пользователя
	premiumUser := &PremiumUser{
		UserID:       userID,
		OrderID:      webhook.Data.ID,
		Email:        webhook.Data.Attributes.UserEmail,
		PurchaseDate: time.Now(),
		IsActive:     true,
	}

	premiumUsers[userID] = premiumUser
	fmt.Printf("Premium user created: %d\n", userID)
}

// Обработка возврата заказа
func handleOrderRefunded(webhook LemonSqueezyWebhook) {
	// Найти пользователя по order_id и деактивировать Premium
	for userID, user := range premiumUsers {
		if user.OrderID == webhook.Data.ID {
			user.IsActive = false
			fmt.Printf("Premium deactivated for user: %d\n", userID)
			break
		}
	}
}

// Пример использования в HTTP сервере
func main() {
	http.HandleFunc("/webhook/lemonsqueezy", handleLemonSqueezyWebhook)

	// Пример создания checkout URL
	http.HandleFunc("/premium/buy", func(w http.ResponseWriter, r *http.Request) {
		userIDStr := r.URL.Query().Get("user_id")
		if userIDStr == "" {
			http.Error(w, "user_id required", http.StatusBadRequest)
			return
		}

		userID, err := strconv.ParseInt(userIDStr, 10, 64)
		if err != nil {
			http.Error(w, "invalid user_id", http.StatusBadRequest)
			return
		}

		checkoutURL, err := createCheckoutURL(userID)
		if err != nil {
			http.Error(w, fmt.Sprintf("Error creating checkout: %v", err), http.StatusInternalServerError)
			return
		}

		http.Redirect(w, r, checkoutURL, http.StatusTemporaryRedirect)
	})

	fmt.Println("Server starting on :8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		panic(err)
	}
}

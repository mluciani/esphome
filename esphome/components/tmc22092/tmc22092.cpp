#include "tmc22092.h"
#include "esphome/core/log.h"

namespace esphome {
namespace tmc {

static const char *TAG = "tmc22092.stepper";

void TMC22092::setup() {
  ESP_LOGCONFIG(TAG, "Setting up TMC22092 '%s'...", this->name_.c_str());
  ESP_LOGD(TAG, "UART Address: 0x%02X", this->uart_address_);

  stepper_driver_ = new TMC22092Stepper(this->get_stream(), sense_resistor_, uart_address_);

  if (stepper_driver_ == nullptr) {
    ESP_LOGE(TAG, "Failed to allocate memory for TMC22092Stepper");
    return;
  }

  ESP_LOGD(TAG, "TMC22092Stepper object created successfully");

  stepper_driver_->pdn_disable(true);
  stepper_driver_->begin();
  stepper_driver_->I_scale_analog(false);
  stepper_driver_->internal_Rsense(false);
  stepper_driver_->mstep_reg_select(true);
  stepper_driver_->en_spreadCycle(false);

  if (reverse_direction_)
    stepper_driver_->shaft(true);

  if (this->sleep_pin_ != nullptr) {
    this->sleep_pin_->setup();
    this->sleep_pin_->digital_write(false);
    this->sleep_pin_state_ = false;
  }
  this->step_pin_->setup();
  this->step_pin_->digital_write(false);
  this->dir_pin_->setup();
  this->dir_pin_->digital_write(false);

  ESP_LOGD(TAG, "TMC22092 setup complete for stepper %s", this->name_.c_str());
}

void TMC22092::dump_config() {
  ESP_LOGCONFIG(TAG, "TMC22092 '%s':", this->name_.c_str());
  LOG_PIN("  Step Pin: ", this->step_pin_);
  LOG_PIN("  Dir Pin: ", this->dir_pin_);
  LOG_PIN("  Sleep Pin: ", this->sleep_pin_);
  ESP_LOGCONFIG(TAG, "  Current Sense Resistor: %.3f", this->sense_resistor_);
  ESP_LOGCONFIG(TAG, "  TMC Address: 0x%02X", this->uart_address_);
  LOG_STEPPER(this);
}
void TMC22092::loop() {
  bool at_target = this->has_reached_target();
  if (this->sleep_pin_ != nullptr) {
    bool sleep_rising_edge = !sleep_pin_state_ & !at_target;
    this->sleep_pin_->digital_write(!at_target);
    this->sleep_pin_state_ = !at_target;
    if (sleep_rising_edge) {
      delayMicroseconds(1000);
    }
  }
  if (at_target) {
    this->high_freq_.stop();
  } else {
    this->high_freq_.start();
  }

  int32_t dir = this->should_step_();
  if (dir == 0)
    return;

  this->dir_pin_->digital_write(dir == 1);
  this->step_pin_->digital_write(true);
  delayMicroseconds(5);
  this->step_pin_->digital_write(false);
}

}  // namespace tmc
}  // namespace esphome
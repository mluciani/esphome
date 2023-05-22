from esphome import automation, pins
from esphome.components import stepper
from esphome.components import uart
import esphome.config_validation as cv
import esphome.codegen as cg
from esphome.const import (
    CONF_CURRENT,
    CONF_DIR_PIN,
    CONF_ID,
    CONF_SLEEP_PIN,
    CONF_STEP_PIN,
)


tmc_ns = cg.esphome_ns.namespace("tmc")
TMC2209 = tmc_ns.class_("TMC2209", stepper.Stepper, cg.Component)
TMC2209SetupAction = tmc_ns.class_("TMC2209SetupAction", automation.Action)

CONF_REVERSE_DIRECTION = "reverse_direction"
CONF_MICROSTEPS = "microsteps"
CONF_TCOOL_THRESHOLD = "tcool_threshold"
CONF_STALL_THRESHOLD = "stall_threshold"
# additional constants for the new configuration parameters
CONF_UART_ADDRESS = "uart_address"
CONF_SENSE_RESISTOR = "sense_resistor"
CONF_STEPPERS = "steppers"

# modify CONFIG_SCHEMA to include the new parameters and to handle multiple steppers
CONFIG_SCHEMA = cv.All(
    cv.Schema({
        cv.Required(CONF_STEPPERS): cv.All(cv.ensure_list(cv.Schema({
            cv.GenerateID(): cv.declare_id(TMC2209),
            cv.Required(CONF_STEP_PIN): pins.gpio_output_pin_schema,
            cv.Required(CONF_DIR_PIN): pins.gpio_output_pin_schema,
            cv.Required(CONF_UART_ADDRESS): cv.hex_uint8_t,
            cv.Required(CONF_SENSE_RESISTOR): cv.resistance,
            cv.Optional(CONF_SLEEP_PIN): pins.gpio_output_pin_schema,
            cv.Optional(CONF_REVERSE_DIRECTION, default=False): cv.boolean,
        }).extend(stepper.STEPPER_SCHEMA)), cv.Length(min=1)),
    }).extend(cv.COMPONENT_SCHEMA)
    .extend(uart.UART_DEVICE_SCHEMA)
)


@automation.register_action(
    "tmc2209.setup",
    TMC2209SetupAction,
    cv.Schema(
        {
            cv.GenerateID(): cv.use_id(TMC2209),
            cv.Required(CONF_UART_ADDRESS): cv.hex_uint8_t,
            cv.Required(CONF_SENSE_RESISTOR): cv.resistance,
            cv.Optional(CONF_MICROSTEPS): cv.templatable(
                cv.one_of(256, 128, 64, 32, 16, 8, 4, 2, 0)
            ),
            cv.Optional(CONF_TCOOL_THRESHOLD): cv.templatable(cv.int_),
            cv.Optional(CONF_STALL_THRESHOLD): cv.templatable(cv.int_),
            cv.Optional(CONF_CURRENT): cv.templatable(cv.current),
        }
    ),
)
def tmc2209_setup_to_code(config, action_id, template_arg, args):
    var = cg.new_Pvariable(action_id, template_arg)
    yield cg.register_parented(var, config[CONF_ID])
    if CONF_MICROSTEPS in config:
        template_ = yield cg.templatable(config[CONF_MICROSTEPS], args, int)
        cg.add(var.set_microsteps(template_))
    if CONF_TCOOL_THRESHOLD in config:
        template_ = yield cg.templatable(config[CONF_TCOOL_THRESHOLD], args, int)
        cg.add(var.set_tcool_threshold(template_))
    if CONF_STALL_THRESHOLD in config:
        template_ = yield cg.templatable(config[CONF_STALL_THRESHOLD], args, int)
        cg.add(var.set_stall_threshold(template_))
    if CONF_CURRENT in config:
        template_ = yield cg.templatable(config[CONF_CURRENT], args, float)
        cg.add(var.set_current(template_))
    if CONF_SENSE_RESISTOR in config:
        template_ = yield cg.templatable(config[CONF_SENSE_RESISTOR], args, float)
        cg.add(var.set_sense_resistor(template_))
    if CONF_UART_ADDRESS in config:
        template_ = yield cg.templatable(config[CONF_UART_ADDRESS], args, int)
        cg.add(var.set_uart_address(template_))

    yield var

# modify to_code to handle multiple steppers and to pass the new parameters
def to_code(config):
    for stepper_config in config[CONF_STEPPERS]:
        step_pin = yield cg.gpio_pin_expression(stepper_config[CONF_STEP_PIN])
        dir_pin = yield cg.gpio_pin_expression(stepper_config[CONF_DIR_PIN])
        uart_address = stepper_config[CONF_UART_ADDRESS]
        sense_resistor = stepper_config[CONF_SENSE_RESISTOR]

        var = cg.new_Pvariable(
            stepper_config[CONF_ID], step_pin, dir_pin, uart_address, sense_resistor, stepper_config[CONF_REVERSE_DIRECTION]
        )
        yield cg.register_component(var, config)
        yield stepper.register_stepper(var, stepper_config)
        yield uart.register_uart_device(var, config)

        if CONF_SLEEP_PIN in stepper_config:
            sleep_pin = yield cg.gpio_pin_expression(stepper_config[CONF_SLEEP_PIN])
            cg.add(var.set_sleep_pin(sleep_pin))

    cg.add_library("SPI", None)
    cg.add_library("teemuatlut/TMCStepper", "0.7.1")

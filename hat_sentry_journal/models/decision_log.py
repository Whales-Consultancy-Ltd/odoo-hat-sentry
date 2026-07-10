from odoo import fields, models


class HatSentryDecisionLog(models.Model):
    _name = "hat_sentry.decision.log"
    _description = "Decision Log"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"
    _order = "id desc"

    name = fields.Char(string="Title", required=True)
    asset_id = fields.Many2one("hat_sentry.asset", string="Asset", index=True)
    decision_type = fields.Selection(
        [("entry", "Entry"), ("exit", "Exit"), ("hold", "Hold"), ("skip", "Skip")],
        string="Decision Type",
        required=True,
    )
    thesis = fields.Text(string="Thesis")
    intended_action = fields.Text(string="Intended Action")
    emotion_level = fields.Selection(
        [(str(i), str(i)) for i in range(1, 6)],
        string="Emotion Level",
        help="1=calm, 5=emotional",
    )
    confidence_level = fields.Selection(
        [(str(i), str(i)) for i in range(1, 6)],
        string="Confidence Level",
        help="1=uncertain, 5=highly confident",
    )
    market_context = fields.Text(string="Market Context")
    entry_criteria = fields.Text(string="Entry Criteria")
    invalidation_level = fields.Text(string="Invalidation Level")
    position_size_rationale = fields.Text(string="Position Size Rationale")
    risk_reward_estimate = fields.Text(string="Risk/Reward Estimate")
    guardrail_warnings = fields.Text(string="Guardrail Warnings")
    outcome = fields.Text(string="Outcome")
    what_went_right = fields.Text(string="What Went Right")
    what_went_wrong = fields.Text(string="What Went Wrong")
    was_plan_followed = fields.Boolean(string="Plan Followed?")
    lesson_learned = fields.Text(string="Lesson Learned")
    trade_id = fields.Many2one("hat_sentry.trade", string="Related Trade", ondelete="set null")
    tag_ids = fields.Many2many("hat_sentry.journal.tag", string="Tags")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    active = fields.Boolean(default=True)

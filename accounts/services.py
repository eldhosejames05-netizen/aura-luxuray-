from django.db import transaction
from django.core.exceptions import ValidationError
from .models import LoyaltyPoints

class LoyaltyService:
    """
    Service layer for managing user loyalty points.
    Encapsulates points accrual, redemption, and cancellation refunds.
    """

    @staticmethod
    @transaction.atomic
    def award_points(user, order):
        """
        Awards points based on dynamic earning_rate.
        """
        # Ensure we don't award points multiple times for the same order
        if LoyaltyPoints.objects.filter(user=user, order=order, transaction_type='Earned').exists():
            return 0

        # Calculate points based on net spent amount and earning_rate
        from .models import LoyaltySettings
        settings = LoyaltySettings.get_settings()
        points_earned = int((order.total_amount // 100) * settings.earning_rate)
        if points_earned > 0:
            LoyaltyPoints.objects.create(
                user=user,
                points=points_earned,
                transaction_type='Earned',
                order=order,
                description=f"Earned points from Order #{order.id}"
            )
            user.loyalty_points += points_earned
            user.save(update_fields=['loyalty_points'])

        return points_earned

    @staticmethod
    @transaction.atomic
    def redeem_points(user, order, points):
        """
        Validates and redeems loyalty points during checkout.
        """
        if points <= 0:
            return

        if user.loyalty_points < points:
            raise ValidationError("Insufficient loyalty points balance.")

        # Create redemption log
        LoyaltyPoints.objects.create(
            user=user,
            points=-points,
            transaction_type='Redeemed',
            order=order,
            description=f"Redeemed points on Order #{order.id}"
        )
        user.loyalty_points -= points
        user.save(update_fields=['loyalty_points'])

    @staticmethod
    @transaction.atomic
    def refund_points(user, order):
        """
        Refunds redeemed points and reverses earned points when an order is cancelled.
        """
        user_updated = False

        # 1. Refund redeemed points
        if hasattr(order, 'points_redeemed') and order.points_redeemed > 0:
            # Check if already refunded
            already_refunded_redeemed = LoyaltyPoints.objects.filter(
                user=user,
                order=order,
                transaction_type='Refunded',
                points=order.points_redeemed
            ).exists()

            if not already_refunded_redeemed:
                LoyaltyPoints.objects.create(
                    user=user,
                    points=order.points_redeemed,
                    transaction_type='Refunded',
                    order=order,
                    description=f"Refunded redeemed points from cancelled Order #{order.id}"
                )
                user.loyalty_points += order.points_redeemed
                user_updated = True

        # 2. Reverse earned points
        earned_tx = LoyaltyPoints.objects.filter(user=user, order=order, transaction_type='Earned').first()
        if earned_tx:
            # Check if already reversed
            already_reversed_earned = LoyaltyPoints.objects.filter(
                user=user,
                order=order,
                transaction_type='Refunded',
                points=-earned_tx.points
            ).exists()

            if not already_reversed_earned:
                LoyaltyPoints.objects.create(
                    user=user,
                    points=-earned_tx.points,
                    transaction_type='Refunded',
                    order=order,
                    description=f"Reversed earned points from cancelled Order #{order.id}"
                )
                user.loyalty_points -= earned_tx.points
                user_updated = True

        if user_updated:
            user.save(update_fields=['loyalty_points'])

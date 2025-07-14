#!/usr/bin/env python3
"""Base classes and utilities for CLI command handling"""
from abc import ABC, abstractmethod
from src.logging.config import get_logger


logger = get_logger(__name__)


class BaseCommand(ABC):
    """Base class for all CLI commands"""

    name = None
    help = None
    description = None

    def __init__(self):
        self.parser = None

    @abstractmethod
    def configure_parser(self, parser):
        """Configure the argument parser for this command"""
        pass

    @abstractmethod
    def execute(self, args):
        """Execute the command with the given arguments"""
        pass

    def register(self, subparsers):
        """Register this command with the given subparsers"""
        if not self.name or not self.help:
            raise ValueError(
                f"Command {self.__class__.__name__} must define name and help attributes"
            )

        self.parser = subparsers.add_parser(
            self.name,
            help=self.help,
            description=self.description or self.help,
        )

        self.configure_parser(self.parser)
        return self.parser

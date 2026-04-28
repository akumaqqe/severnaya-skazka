from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils import timezone

from .models import Choice, LearningResult, Poll


User = get_user_model()


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label="Имя", required=False)
    last_name = forms.CharField(max_length=150, label="Фамилия", required=False)
    email = forms.EmailField(label="Электронная почта", required=False)
    age = forms.IntegerField(min_value=6, max_value=11, label="Возраст")
    class_group = forms.CharField(max_length=100, label="Класс / группа")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "age",
            "class_group",
            "password1",
            "password2",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile = user.profile
            profile.age = self.cleaned_data["age"]
            profile.class_group = self.cleaned_data["class_group"]
            profile.save()
        return user


class VoteForm(forms.Form):
    choice = forms.ModelChoiceField(
        queryset=Choice.objects.none(),
        label="Выберите вариант ответа",
        empty_label=None,
        widget=forms.RadioSelect,
    )

    def __init__(self, poll, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.poll = poll
        self.fields["choice"].queryset = poll.choices.order_by("id")

    def clean_choice(self):
        choice = self.cleaned_data["choice"]
        if choice.poll_id != self.poll.id:
            raise forms.ValidationError("Выбран неверный вариант ответа.")
        return choice


class LearningResultForm(forms.ModelForm):
    class Meta:
        model = LearningResult
        fields = ("stage_title", "points", "is_successful")
        labels = {
            "stage_title": "Название этапа / задания",
            "points": "Баллы",
            "is_successful": "Задание успешно выполнено",
        }
        widgets = {
            "stage_title": forms.TextInput(
                attrs={"placeholder": "Например: Северный орнамент"}
            ),
            "points": forms.NumberInput(attrs={"min": 0, "max": 1000}),
        }


class PollForm(forms.ModelForm):
    end_date = forms.DateTimeField(
        label="Дата окончания",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    class Meta:
        model = Poll
        fields = ("title", "description", "end_date", "is_active")
        labels = {
            "title": "Название голосования",
            "description": "Описание",
            "is_active": "Голосование активно",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.end_date:
            local_dt = timezone.localtime(self.instance.end_date)
            self.initial["end_date"] = local_dt.strftime("%Y-%m-%dT%H:%M")

    def clean(self):
        cleaned_data = super().clean()
        end_date = cleaned_data.get("end_date")
        is_active = cleaned_data.get("is_active")
        if end_date and is_active and end_date <= timezone.now():
            self.add_error(
                "end_date",
                "Для активного голосования дата окончания должна быть в будущем.",
            )
        return cleaned_data


class BaseChoiceInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        normalized_texts = set()
        active_forms = 0

        for form in self.forms:
            if not hasattr(form, "cleaned_data") or not form.cleaned_data:
                continue

            marked_for_delete = form.cleaned_data.get("DELETE")
            text = (form.cleaned_data.get("text") or "").strip()

            if marked_for_delete:
                if form.instance.pk and form.instance.votes_count > 0:
                    raise forms.ValidationError(
                        "Нельзя удалить вариант ответа, по которому уже есть голоса."
                    )
                continue

            if text:
                normalized_text = text.lower()
                if normalized_text in normalized_texts:
                    raise forms.ValidationError(
                        "В одном голосовании варианты ответа должны быть уникальны."
                    )
                normalized_texts.add(normalized_text)
                active_forms += 1

        if active_forms < 2:
            raise forms.ValidationError(
                "Добавьте минимум два варианта ответа для голосования."
            )


ChoiceFormSet = inlineformset_factory(
    Poll,
    Choice,
    fields=("text",),
    extra=2,
    can_delete=True,
    min_num=2,
    validate_min=True,
    formset=BaseChoiceInlineFormSet,
    widgets={
        "text": forms.TextInput(attrs={"placeholder": "Введите вариант ответа"}),
    },
)

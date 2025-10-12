import { useEffect, useRef } from 'react';
import feather from 'feather-icons';
import useOnScreen from '../hooks/useOnScreen.ts';

interface FeatureCardProps {
    icon: string;
    title: string;
    description: string;
    delay: string;
}

const FeatureCard = ({ icon, title, description, delay }: FeatureCardProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const isVisible = useOnScreen(ref, '-100px');

    useEffect(() => {
        if (isVisible) {
            feather.replace();
        }
    }, [isVisible]);

    return (
        <div
            ref={ref}
            className={`flex flex-col items-center transition-all duration-700 p-4 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-5'}`}
            style={{ transitionDelay: `${delay}ms` }}
        >
            <div className="p-4 bg-white-200 outline rounded-full mb-4">
                <i data-feather={icon} className="w-6 h-6 text-red-700"></i>
            </div>
            <h3 className="font-semibold text-lg mb-2">{title}</h3>
            <p className="text-gray-800 text-sm">{description}</p>
        </div>
    );
};

export default FeatureCard;